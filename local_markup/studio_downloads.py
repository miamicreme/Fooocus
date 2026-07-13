from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from time import time_ns

from local_markup.studio_history import StudioHistoryStore


DOWNLOAD_DIR = Path(gettempdir()) / "fooocus_ai_studio_downloads"


def ensure_download_dir() -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return DOWNLOAD_DIR


def safe_download_name(prefix: str, extension: str = "txt") -> str:
    unique_stamp = time_ns()
    cleaned_prefix = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in prefix).strip("_") or "studio"
    return f"{cleaned_prefix}_{unique_stamp}.{extension}"


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


def write_result_manifest(output_paths: list[str], status_message: str = "") -> str:
    path = ensure_download_dir() / safe_download_name("fooocus_result_manifest")
    lines = ["Fooocus AI Studio Result Manifest", "", status_message or "No status message.", "", "Outputs:"]
    lines.extend([f"- {output_path}" for output_path in output_paths] or ["- No outputs returned yet."])
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def latest_downloadable_result(output_paths: list[str]) -> str | None:
    for output_path in reversed(output_paths):
        if output_path and Path(output_path).exists():
            return output_path
    return None


def history_gallery_markdown(store: StudioHistoryStore) -> str:
    if not store.items:
        return "## History Gallery\n\nNo generated images are recorded yet. After live generation, saved images will appear here with download buttons."
    rows = ["## History Gallery", "", "| Item | Workflow | Images | Rating |", "|---|---|---|---|"]
    for item in store.latest(limit=12):
        output_paths = item.image_paths or ([item.image_path] if item.image_path else [])
        image_text = "<br>".join(output_paths) if output_paths else "No image returned yet"
        rating = "unrated" if item.rating is None else str(item.rating)
        rows.append(f"| `{item.item_id}` | `{item.workflow}` | {image_text} | `{rating}` |")
    return "\n".join(rows)
