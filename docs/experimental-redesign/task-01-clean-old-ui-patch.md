# Task 1: Clean Local Fooocus Launch

Branch: `cleanup/remove-old-ui-patch`

This task keeps Fooocus as the stable local engine and keeps AI Studio separate as the planning/control layer.

## What Was Checked

`RUN_FOOOCUS_LOCAL.bat` already does the required safe startup behavior:

```bat
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe
set GRADIO_ANALYTICS_ENABLED=False
set GRADIO_VERSION_CHECK=False
%PYTHON_CMD% scripts\remove_easy_sdxl_webui.py
%PYTHON_CMD% launch.py --disable-analytics --listen
```

This means the local runner:

- uses the repo virtual environment when available,
- suppresses Gradio analytics/version noise,
- runs the old UI patch cleanup script before launch,
- does not apply new UI patches to `webui.py`,
- tells users to use `RUN_AI_STUDIO.bat` for the separate Studio UI.

## Cleanup Script

The cleanup script is:

```text
scripts/remove_easy_sdxl_webui.py
```

It removes old marked blocks from `webui.py` using these markers:

```text
# EASY_SDXL_WEBUI_HELPER_START / # EASY_SDXL_WEBUI_HELPER_END
# EASY_SDXL_WEBUI_PANEL_START / # EASY_SDXL_WEBUI_PANEL_END
# EASY_SDXL_WEBUI_BINDING_START / # EASY_SDXL_WEBUI_BINDING_END
```

The script is idempotent because it loops through existing marker blocks and prints a no-op message when none are found.

## Validation Commands

Run from repo root on Windows:

```powershell
python scripts\remove_easy_sdxl_webui.py
python scripts\remove_easy_sdxl_webui.py
python -m py_compile webui.py
.\RUN_FOOOCUS_LOCAL.bat
```

Expected result:

- First script run removes old blocks if present or reports none found.
- Second script run reports none found.
- `webui.py` compiles.
- Fooocus launches normally.
- No old experimental helper panel appears.

## Stop Conditions

Stop and fix this branch before continuing if:

- `webui.py` fails to compile,
- Fooocus no longer starts,
- old helper UI appears,
- the cleanup script is not safe to run twice.

## Next Branch

After local launch is verified, continue with:

```text
studio/v2-planner
```
