import gradio as gr

from local_markup.studio_workflow_controller import build_studio_workflow_outputs
from local_markup.fooocus_feature_playbook import build_feature_reasoning
from local_markup.fooocus_feature_catalog import list_features_markdown
from local_markup.style_explainer import describe_style_markdown, list_style_names, style_recommendations_for_goal
from local_markup.studio_usage_guide import studio_usage_markdown
from local_markup.studio_control_ui import CONTROL_UI_CSS, history_gallery_empty_note, studio_hero_markdown
from local_markup.studio_copy_controls import copy_controls_summary
from local_markup.studio_downloads import write_history_download, write_prompt_pack


STYLE_NAMES = list_style_names()


def copyable_textbox(**kwargs):
    return gr.Textbox(show_copy_button=True, **kwargs)


def explain_style(style_name, goal):
    return describe_style_markdown(style_name, goal or "realistic personal photo")


def recommend_styles(goal):
    return style_recommendations_for_goal(goal or "realistic personal photo")


def explain_feature_stack(goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle):
    image_count = sum(x is not None for x in [image_1, image_2, image_3])
    return build_feature_reasoning(goal, image_count, wants_identity, wants_exact_edit, wants_bundle)


def feature_catalog_markdown():
    return list_features_markdown()


def build_app():
    with gr.Blocks(title="AI Image Studio", css=CONTROL_UI_CSS) as demo:
        gr.HTML(value=studio_hero_markdown())

        with gr.Tab("Studio Control Center"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(
                        "## Create the plan\n"
                        "Start here. The Studio is stable even if the local Fooocus engine is not running yet."
                    )
                    with gr.Accordion("Fast no-friction instructions", open=True):
                        gr.Markdown(value=studio_usage_markdown())
                    goal = copyable_textbox(
                        label="What image do you want?",
                        placeholder="Example: realistic full-body resort pool photo, keep my face recognizable, clean luxury lifestyle look",
                        lines=5,
                    )
                    with gr.Accordion("Optional controls", open=False):
                        wants_identity = gr.Checkbox(label="Keep same person or subject", value=True)
                        wants_exact_edit = gr.Checkbox(label="Edit only a specific image or masked area", value=False)
                        wants_bundle = gr.Checkbox(label="Plan a small shot set after the first image", value=False)
                        vram_gb = gr.Slider(label="GPU VRAM in GB", minimum=4, maximum=24, value=6, step=1)
                    plan_btn = gr.Button("Build My Fooocus Plan", variant="primary")

                with gr.Column(scale=1):
                    gr.Markdown("## References\nUpload only what matters. Extra images create churn.")
                    image_1 = gr.Image(label="Reference 1: main subject, source image, or face", type="numpy")
                    image_2 = gr.Image(label="Reference 2: optional mask, style, or support image", type="numpy")
                    image_3 = gr.Image(label="Reference 3: optional pose, layout, or extra angle", type="numpy")

            gr.Markdown(value=copy_controls_summary())
            with gr.Row():
                selected_tool = copyable_textbox(label="Use this Fooocus workflow", interactive=False)
                selected_area = copyable_textbox(label="Open this Fooocus tab or area", interactive=False)

            with gr.Row():
                primary_prompt = copyable_textbox(label="Step 1: Copy this prompt", lines=7)
                negative_prompt = copyable_textbox(label="Step 2: Copy this negative prompt", lines=7)

            with gr.Row():
                handoff_recipe = copyable_textbox(label="Step 3: Follow these Fooocus setup steps", lines=10)
                shot_prompts = copyable_textbox(label="Use these only after the first result", lines=10)

            with gr.Accordion("Review before generating", open=True):
                adapter_preview = gr.Markdown(label="Adapter preview")
                history_preview = gr.Markdown(label="History preview")

            with gr.Row():
                download_prompt_pack_btn = gr.Button("Download Prompt Pack", variant="secondary")
                download_history_btn = gr.Button("Download Session History", variant="secondary")
            with gr.Row():
                prompt_pack_file = gr.File(label="Prompt pack download")
                history_file = gr.File(label="Session history download")

            with gr.Accordion("History gallery and image downloads", open=True):
                gr.Markdown(value=history_gallery_empty_note())
                gr.Gallery(label="Generated image history", value=[], visible=True, columns=4, height=320)
                gr.Markdown(
                    "Image download buttons will appear here after live generation output is connected. "
                    "For now, use **Download Prompt Pack** and **Download Session History**."
                )

            with gr.Accordion("Engine status", open=False):
                gr.Markdown(
                    "The local Fooocus engine is intentionally not embedded here while it is unstable on this machine.\n\n"
                    "Use `RUN_FOOOCUS_ENGINE_ONLY.bat` to test the engine separately. Keep working in this Studio at `http://127.0.0.1:7872`."
                )

            with gr.Accordion("Full reasoning", open=False):
                agent_plan = gr.Markdown(label="Agent plan")

            plan_btn.click(
                build_studio_workflow_outputs,
                inputs=[goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle, vram_gb],
                outputs=[agent_plan, primary_prompt, negative_prompt, selected_tool, selected_area, shot_prompts, handoff_recipe, adapter_preview, history_preview],
                queue=False,
            )
            download_prompt_pack_btn.click(
                write_prompt_pack,
                inputs=[selected_tool, selected_area, primary_prompt, negative_prompt, handoff_recipe, shot_prompts],
                outputs=prompt_pack_file,
                queue=False,
            )
            download_history_btn.click(
                write_history_download,
                inputs=history_preview,
                outputs=history_file,
                queue=False,
            )

        with gr.Tab("Feature Brain"):
            gr.Markdown(
                "## Feature Brain\n"
                "Use this when you want to understand why the Studio chose a Fooocus feature."
            )
            feature_btn = gr.Button("Explain Feature Stack", variant="primary")
            feature_stack = gr.Markdown()
            feature_btn.click(
                explain_feature_stack,
                inputs=[goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle],
                outputs=feature_stack,
                queue=False,
            )
            with gr.Accordion("Full source-of-truth feature catalog", open=False):
                catalog = gr.Markdown(value=feature_catalog_markdown())

        with gr.Tab("Style Coach"):
            gr.Markdown("Use this before generating if you need help choosing a Fooocus style.")
            with gr.Row():
                with gr.Column():
                    style_name = gr.Dropdown(label="Style", choices=STYLE_NAMES, value="Fooocus Photograph")
                    style_goal = copyable_textbox(label="Image goal", value="realistic personal photo", lines=3)
                    explain_btn = gr.Button("Explain Style", variant="primary")
                    recommend_btn = gr.Button("Recommend Styles")
                with gr.Column():
                    style_explanation = gr.Markdown()
                    style_recs = copyable_textbox(label="Recommended styles", lines=8)
            explain_btn.click(explain_style, inputs=[style_name, style_goal], outputs=style_explanation, queue=False)
            recommend_btn.click(recommend_styles, inputs=style_goal, outputs=style_recs, queue=False)

        with gr.Tab("How to Use"):
            gr.Markdown(
                "## How to use this control UI\n\n"
                "1. Run `RUN_STUDIO_ONE_UI.bat`.\n"
                "2. Work from `http://127.0.0.1:7872`.\n"
                "3. Use **Studio Control Center** first.\n"
                "4. Click **Build My Fooocus Plan**.\n"
                "5. Use copy buttons on every output box.\n"
                "6. Download the prompt pack.\n"
                "7. Test the Fooocus engine separately only when needed with `RUN_FOOOCUS_ENGINE_ONLY.bat`.\n\n"
                "This keeps the Studio stable while the local engine issue is isolated."
            )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7872, inbrowser=False)
