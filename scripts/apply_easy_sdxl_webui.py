from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEBUI = ROOT / "webui.py"

HELPER_START = "# EASY_SDXL_WEBUI_HELPER_START"
HELPER_END = "# EASY_SDXL_WEBUI_HELPER_END"
PANEL_START = "# EASY_SDXL_WEBUI_PANEL_START"
PANEL_END = "# EASY_SDXL_WEBUI_PANEL_END"
BINDING_START = "# EASY_SDXL_WEBUI_BINDING_START"
BINDING_END = "# EASY_SDXL_WEBUI_BINDING_END"

HELPER = r'''
# EASY_SDXL_WEBUI_HELPER_START
def easy_sdxl_webui_plan(instruction, goal):
    from local_markup.easy_sdxl import build_easy_sdxl_outputs
    from local_markup.photo_bundle import build_bundle_plan
    from local_markup.style_explainer import style_recommendations_for_goal

    text = (instruction or "").strip()
    if not text:
        text = "Remove only the jacket. Keep the same person, same face, same pose, and same background. Replace the jacket area with a clean professional shirt."

    if goal == "Swimming / resort bundle":
        plan = build_bundle_plan("Swimming / Resort", "swimwear", text or "make me standing near a pool ready for swimming")
        guide = plan.as_text()
        return plan.identity_prompt, "", "", plan.negative_prompt, guide, True, True

    if goal == "Stand up full-body":
        plan = build_bundle_plan("Lifestyle Starter", "casual", text or "standing full-body realistic portrait")
        guide = plan.as_text()
        return plan.identity_prompt, "", "", plan.negative_prompt, guide, True, True

    area = "Shirt / Clothes"
    if goal == "Remove glasses":
        area = "Glasses"
    elif goal == "Change background":
        area = "Background"
    elif goal == "Improve face/headshot":
        area = "Face"
    elif goal == "Swimwear outfit":
        area = "Shirt / Clothes"
        text = text or "replace clothing with tasteful swim trunks suitable for swimming, non-explicit, natural fit"

    positive, inpaint, detection, negative, settings, checklist = build_easy_sdxl_outputs("Edit This Image", area, text)

    if goal == "Remove jacket":
        detection = "jacket, suit jacket, blazer, coat"
        inpaint = "same person, preserve facial identity, age, skin tone, expression, camera angle, and lighting, remove only the jacket, replace the jacket area with a clean professional shirt, professional realistic headshot, seamless edit, natural fabric texture, no visible retouching artifacts"
        positive = inpaint
    elif goal == "Swimwear outfit":
        detection = "shirt, jacket, clothing, outfit"
        inpaint = "same adult person, preserve facial identity, age, skin tone, face shape, expression, camera angle, and lighting, wearing tasteful swim trunks suitable for swimming, beach or pool ready, non-explicit, natural fit, realistic body proportions, professional realistic lifestyle photo, seamless clothing edit"
        positive = inpaint
        negative = negative + ", nude, explicit nudity, see-through clothing, sexualized pose"

    guide = (
        "Easy SDXL plan ready. Use Inpaint or Outpaint for exact edits. "
        "Upload the image, enable Advanced Masking Features, use SAM, click Generate mask from image, review the mask, then Generate.\n\n"
        + checklist
        + "\n\nStyle advice:\n"
        + style_recommendations_for_goal(text)
    )
    return positive, inpaint, detection, negative, guide, True, True
# EASY_SDXL_WEBUI_HELPER_END
'''

PANEL = r'''
                    # EASY_SDXL_WEBUI_PANEL_START
                    with gr.Accordion("Easy SDXL Exact Edit + Photo Bundle", open=True):
                        gr.Markdown("One place for exact edits and safe personal photo bundles. This writes directly into Fooocus prompt, inpaint prompt, negative prompt, and SAM detection prompt.")
                        with gr.Row():
                            easy_sdxl_goal = gr.Radio(
                                label="One-click goal",
                                choices=["Remove jacket", "Remove glasses", "Change clothing", "Swimwear outfit", "Stand up full-body", "Swimming / resort bundle", "Change background", "Improve face/headshot"],
                                value="Remove jacket",
                            )
                            easy_sdxl_instruction = gr.Textbox(
                                label="Plain-English edit or bundle goal",
                                value="Remove only the jacket. Keep the same person, same face, same pose, same background, and replace the jacket area with a clean professional shirt.",
                                lines=3,
                            )
                        easy_sdxl_apply = gr.Button(value="Plan Exact Edit / Bundle", variant="primary")
                        easy_sdxl_guide = gr.Textbox(label="Exact edit guide, bundle plan, and style expectations", lines=12, interactive=False)
                    # EASY_SDXL_WEBUI_PANEL_END
'''

BINDING = r'''
        # EASY_SDXL_WEBUI_BINDING_START
        easy_sdxl_apply.click(
            easy_sdxl_webui_plan,
            inputs=[easy_sdxl_instruction, easy_sdxl_goal],
            outputs=[
                prompt,
                inpaint_additional_prompt,
                inpaint_mask_dino_prompt_text,
                negative_prompt,
                easy_sdxl_guide,
                input_image_checkbox,
                inpaint_advanced_masking_checkbox,
            ],
            queue=False,
            show_progress=False,
        )
        # EASY_SDXL_WEBUI_BINDING_END
'''


def replace_marked_block(text: str, start: str, end: str, replacement: str) -> tuple[str, bool]:
    start_index = text.find(start)
    if start_index == -1:
        return text, False
    block_start = text.rfind("\n", 0, start_index)
    if block_start == -1:
        block_start = start_index
    block_end = text.find(end, start_index)
    if block_end == -1:
        return text, False
    block_end = text.find("\n", block_end)
    if block_end == -1:
        block_end = len(text)
    new_text = text[:block_start] + "\n" + replacement + text[block_end:]
    return new_text, new_text != text


def main():
    text = WEBUI.read_text(encoding="utf-8")
    changed = False

    text, did_replace = replace_marked_block(text, HELPER_START, HELPER_END, HELPER)
    changed = changed or did_replace
    text, did_replace = replace_marked_block(text, PANEL_START, PANEL_END, PANEL)
    changed = changed or did_replace
    text, did_replace = replace_marked_block(text, BINDING_START, BINDING_END, BINDING)
    changed = changed or did_replace

    if HELPER_START not in text:
        text = text.replace("reload_javascript()", HELPER + "\nreload_javascript()", 1)
        changed = True

    if PANEL_START not in text:
        anchor = "                    if isinstance(default_prompt, str) and default_prompt != '':\n                        shared.gradio_root.load(lambda: default_prompt, outputs=prompt)\n"
        text = text.replace(anchor, anchor + PANEL, 1)
        changed = True

    if BINDING_START not in text:
        anchor = "        inpaint_mode.change(inpaint_mode_change, inputs=[inpaint_mode, inpaint_engine_state], outputs=[\n            inpaint_additional_prompt, outpaint_selections, example_inpaint_prompts,\n            inpaint_disable_initial_latent, inpaint_engine,\n            inpaint_strength, inpaint_respective_field\n        ], show_progress=False, queue=False)\n"
        text = text.replace(anchor, anchor + BINDING, 1)
        changed = True

    if changed:
        WEBUI.write_text(text, encoding="utf-8")
        print("Easy SDXL WebUI integration applied/repaired.")
    else:
        print("Easy SDXL WebUI integration already healthy.")


if __name__ == "__main__":
    main()
