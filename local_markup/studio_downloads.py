from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from time import time

from local_markup.studio_history import StudioHistoryStore


DOWNLOAD_DIR = Path(gettempdir()) / "fooocus_ai_studio_downloads"


def ensure_download_dir() -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return DOWNLOAD_DIR


def safe_download_name(prefix: str, extension: str = "txt") -> str:
    timestamp = int(time())
    cleaned_prefix = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in prefix).strip("_") or "studio"
    return f"{cleaned_prefix}_{timestamp}.{extension}"


def build_prompt_pack_text(
    workflow: str,
    fooocus_area: str,
    prompt: str,
    negative_prompt: str,
    setup_steps: str,
    next_shots: str,
) -> str:
    return "\n\n".join(
        [
            "Fooocus AI Studio Prompt Pack",
            f"Workflow: {workflow}",
            f"Fooocus Area: {fooocus_area}",
            "Prompt:",
            prompt or "",
            "Negative Prompt:",
            negative_prompt or "",
            "Setup Steps:",
            setup_steps or "",
            "Next Shots:",
            next_shots or "",
        ]
    )


def build_engine_handoff_text(
    workflow: str,
    fooocus_area: str,
    prompt: str,
    negative_prompt: str,
    setup_steps: str,
    next_shots: str,
) -> str:
    if not any([workflow, fooocus_area, prompt, negative_prompt, setup_steps, next_shots]):
        return "Build your Fooocus plan first, then click Send to Engine."

    return "\n\n".join(
        [
            "Send to Engine Handoff",
            (
                "Browser safety note: AI Studio cannot directly auto-fill the embedded Fooocus "
                "engine fields because the engine runs on a different local port. This prepares "
                "the exact fields on the same page so you can paste them into the hidden engine safely."
            ),
            f"1. Open Fooocus area: {fooocus_area or 'Use the selected Fooocus area from the plan.'}",
            f"2. Workflow: {workflow or 'Use the selected workflow from the plan.'}",
            "3. Prompt:",
            prompt or "Build the plan first to generate a prompt.",
            "4. Negative Prompt:",
            negative_prompt or "Build the plan first to generate a negative prompt.",
            "5. Setup Steps:",
            setup_steps or "Follow the Studio setup steps after building the plan.",
            "6. Next Shot Prompts:",
            next_shots or "Generate one first image, review it, then continue.",
        ]
    )


def write_prompt_pack(
    workflow: str,
    fooocus_area: str,
    prompt: str,
    negative_prompt: str,
    setup_steps: str,
    next_shots: str,
) -> str:
    path = ensure_download_dir() / safe_download_name("fooocus_prompt_pack")
    path.write_text(
        build_prompt_pack_text(workflow, fooocus_area, prompt, negative_prompt, setup_steps, next_shots),
        encoding="utf-8",
    )
    return str(path)


def build_history_text(history_markdown: str) -> str:
    return "Fooocus AI Studio History\n\n" + (history_markdown or "No session history recorded yet.")


def write_history_download(history_markdown: str) -> str:
    path = ensure_download_dir() / safe_download_name("fooocus_history")
    path.write_text(build_history_text(history_markdown), encoding="utf-8")
    return str(path)


def history_gallery_markdown(store: StudioHistoryStore) -> str:
    if not store.items:
        return "## History Gallery\n\nNo generated images are recorded yet. After live generation is wired, saved images will appear here with download buttons."

    rows = ["## History Gallery", "", "| Item | Workflow | Image | Rating |", "|---|---|---|---|"]
    for item in store.latest(limit=12):
        image_path = item.image_path or "Pending manual save"
        rating = "unrated" if item.rating is None else str(item.rating)
        rows.append(f"| `{item.item_id}` | `{item.workflow}` | `{image_path}` | `{rating}` |")
    return "\n".join(rows)
