from __future__ import annotations


CONTROL_UI_CSS = """
.studio-hero {
    padding: 18px 20px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(20,20,24,0.95), rgba(45,45,58,0.9));
    border: 1px solid rgba(255,255,255,0.12);
}
.studio-card {
    padding: 14px 16px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.04);
}
.studio-small {
    opacity: 0.82;
    font-size: 0.95em;
}
"""


def studio_hero_markdown() -> str:
    return (
        "<div class='studio-hero'>"
        "<h1>AI Image Studio Control Center</h1>"
        "<p>Describe the image, copy the prepared fields, and use the hidden Fooocus engine only when you are ready to generate.</p>"
        "<p class='studio-small'>No friction: one goal, one first shot, one review cycle.</p>"
        "</div>"
    )


def engine_hidden_note() -> str:
    return (
        "## Engine is hidden by default\n\n"
        "Use the Studio controls first. Open the engine panel only when you need to paste and generate."
    )


def history_gallery_empty_note() -> str:
    return (
        "## History Gallery\n\n"
        "Image downloads appear here after generated outputs are connected. For now, use the prompt pack and session history downloads."
    )
