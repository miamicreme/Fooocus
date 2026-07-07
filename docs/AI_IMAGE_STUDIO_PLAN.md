# AI Image Studio Plan

## Why this exists

Patching Fooocus `webui.py` directly is brittle. The correct architecture is to keep Fooocus as the SDXL engine and build a clean AI-assisted control interface beside it.

## New files

```txt
ai_studio_app.py
local_markup/ai_studio_agent.py
RUN_AI_STUDIO.bat
docs/AI_IMAGE_STUDIO_PLAN.md
```

## Current version

The current AI Studio is a standalone Gradio app at:

```txt
http://127.0.0.1:7872
```

It does not modify Fooocus core UI. It helps the user decide which workflow to use and prepares the prompt, negative prompt, reference strategy, mask strategy, and next steps.

## User flow

1. Start Fooocus normally with `RUN_FOOOCUS_LOCAL.bat`.
2. Start the new AI Studio with `RUN_AI_STUDIO.bat`.
3. Upload 1-3 reference/source images into AI Studio.
4. Tell the agent the goal.
5. The agent selects the workflow:
   - Text to Image
   - Inpaint / Outpaint
   - Image Prompt / Face Reference
   - PyraCanny / CPDS
   - Upscale / Variation
   - Bundle Builder
6. The user reviews the plan and uses Fooocus as the engine.

## What the agent does

The agent infers:

- whether the task is an exact edit
- whether identity preservation matters
- whether a photo bundle is being requested
- whether structure/pose/composition control is needed
- whether upscale/variation is the right path
- whether masks are required

It outputs:

- selected tool
- Fooocus area
- primary prompt
- negative prompt
- reference strategy
- mask strategy
- recommended settings
- next steps
- warnings / guardrails

## Why this is safer

The new UI does not monkey-patch Fooocus UI. It can be iterated quickly and tested separately.

## Next engineering phase

Add a backend adapter that can submit jobs directly to:

1. Local Fooocus through a stable API/queue adapter, or
2. RunPod / remote worker through a provider adapter.

That would remove hand-off/copy-paste entirely.

## Future architecture

```txt
AI Image Studio UI
        ↓
Workflow Agent
        ↓
Job API / Queue
        ↓
Provider Adapter
        ↓
Fooocus Local OR RunPod Worker
        ↓
Gallery / History / Metadata
```

## Guardrails

Guardrails should live in the job API / task boundary, not only in the UI. The Studio Agent should advise, but backend validation must enforce.
