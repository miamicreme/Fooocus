# Task 34: Designed Control UI

Branch: `studio/designed-control-ui`

## Goal

Replace the two-page feeling with a cleaner control center:

- Studio controls are the primary UI.
- The raw Fooocus engine is hidden by default.
- Copy-ready text boxes still have copy buttons.
- Prompt pack and session history have download buttons.
- A history gallery area is visible and ready for generated image downloads later.

## Completed

Added:

```text
local_markup/studio_control_ui.py
local_markup/studio_downloads.py
tests/test_studio_control_ui.py
tests/test_studio_downloads.py
tests/test_ai_studio_app_designed_control_ui.py
tests/test_launch_util_temp_cleanup.py
scripts/run_fooocus_keepalive.py
scripts/run_studio_one_ui.ps1
```

Updated:

```text
ai_studio_app.py
tests/test_ai_studio_app_one_ui_copy.py
tests/test_one_ui_launcher_exists.py
modules/launch_util.py
RUN_STUDIO_ONE_UI.bat
```

## Startup Fixes

`delete_folder_content()` now recreates the temp folder if it is missing. This prevents startup from crashing when `C:\Users\<user>\AppData\Local\Temp\fooocus` was already removed or never existed.

`RUN_STUDIO_ONE_UI.bat` now routes through `scripts/run_studio_one_ui.ps1`, which:

- starts Fooocus first,
- waits an initial engine warmup delay,
- waits for port `7865` before opening Studio,
- starts Studio after the engine wait,
- waits for port `7872`,
- opens the browser only after Studio is ready.

Defaults:

```text
InitialEngineDelaySeconds = 45
EngineWaitSeconds = 420
StudioWaitSeconds = 120
```

## User Flow

1. Run `RUN_STUDIO_ONE_UI.bat`.
2. Wait for the launcher to report that Studio is ready.
3. Open/use `http://127.0.0.1:7872`.
4. Use **Studio Control Center**.
5. Describe the image.
6. Click **Build My Fooocus Plan**.
7. Use copy buttons on the outputs.
8. Download the prompt pack if needed.
9. Open **Hidden Fooocus engine** only when ready to paste and generate.
10. Use **Download Session History** to save the plan/history.

## Runtime Boundary

The engine is visually hidden, not removed. The UI does not directly call the Fooocus worker yet. This is still a safe manual handoff.

## Validation

```powershell
python -m py_compile ai_studio_app.py local_markup\studio_control_ui.py local_markup\studio_downloads.py modules\launch_util.py scripts\run_fooocus_keepalive.py
python -m pytest tests/test_studio_control_ui.py tests/test_studio_downloads.py tests/test_ai_studio_app_designed_control_ui.py tests/test_ai_studio_app_one_ui_copy.py tests/test_launch_util_temp_cleanup.py tests/test_one_ui_launcher_exists.py -q
```
