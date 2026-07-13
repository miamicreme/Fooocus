import gradio as gr

from local_markup.studio_workflow_controller import (
    build_studio_workflow_outputs,
    load_generation_results,
    stop_studio_generation,
    submit_studio_enhancement,
    submit_studio_generation,
    use_latest_result_as_reference,
)
from local_markup.fooocus_feature_playbook import build_feature_reasoning
from local_markup.fooocus_feature_catalog import list_features_markdown
from local_markup.style_explainer import describe_style_markdown, list_style_names, style_recommendations_for_goal
from local_markup.studio_usage_guide import studio_usage_markdown
from local_markup.studio_control_ui import CONTROL_UI_CSS, studio_hero_markdown
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


def open_history_message():
    return "## History opened\n\nUse the gallery below for recent Studio outputs and the history download for the full session record."


def build_app():
    with gr.Blocks(title="AI Image Studio", css=CONTROL_UI_CSS) as demo:
        gr.HTML(value=studio_hero_markdown())

        with gr.Tab("Studio Control Center"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(
                        "## Create and generate\n"
                        "One UI only: enter the image goal, add references, then click **Generate in Studio**."
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
                    plan_btn = gr.Button("Build My Fooocus Plan", variant="secondary")
                    generate_btn = gr.Button("Generate in Studio", variant="primary")

                with gr.Column(scale=1):
                    gr.Markdown("## References\nUpload only what matters. Studio sends these images directly to the local engine.")
                    image_1 = gr.Image(label="Reference 1: main subject, source image, or face", type="filepath")
                    image_2 = gr.Image(label="Reference 2: optional mask, style, or support image", type="filepath")
                    image_3 = gr.Image(label="Reference 3: optional pose, layout, or extra angle", type="filepath")

            gr.Markdown(value=copy_controls_summary())
            gr.Markdown("Copy controls are fallback/debugging tools. Normal generation stays entirely inside Studio.")
            with gr.Row():
                selected_tool = copyable_textbox(label="Selected Studio workflow", interactive=False)
                selected_area = copyable_textbox(label="Fooocus engine area", interactive=False)

            with gr.Row():
                primary_prompt = copyable_textbox(label="Primary prompt used by Generate", lines=7)
                negative_prompt = copyable_textbox(label="Negative prompt used by Generate", lines=7)

            with gr.Row():
                handoff_recipe = copyable_textbox(label="Manual fallback steps", lines=10)
                shot_prompts = copyable_textbox(label="Use these only after the first result", lines=10)

            with gr.Accordion("Generate controls", open=True):
                generation_status = gr.Markdown(value="## Generation status\n\nReady. Build a plan or click **Generate in Studio**.")
                active_job_id = gr.Textbox(visible=False)
                with gr.Row():
                    stop_btn = gr.Button("Stop", variant="stop")
                    regenerate_btn = gr.Button("Regenerate", variant="secondary")
                    enhance_btn = gr.Button("Enhance", variant="secondary")
                    use_reference_btn = gr.Button("Use as Reference", variant="secondary")
                    open_history_btn = gr.Button("Open in History", variant="secondary")
                with gr.Row():
                    latest_result_file = gr.File(label="Download latest result or manifest")
                    latest_result_path = copyable_textbox(label="Copy latest result path", interactive=False)

            with gr.Accordion("Results gallery", open=True):
                generation_gallery = gr.Gallery(label="Generated image history", value=[], visible=True, columns=4, height=360)

            with gr.Accordion("Review before generating", open=True):
                adapter_preview = gr.Markdown(label="Adapter preview")
                history_preview = gr.Markdown(label="History preview")

            with gr.Row():
                download_prompt_pack_btn = gr.Button("Download Prompt Pack", variant="secondary")
                download_history_btn = gr.Button("Download Session History", variant="secondary")
                refresh_results_btn = gr.Button("Refresh Gallery", variant="secondary")
            with gr.Row():
                prompt_pack_file = gr.File(label="Prompt pack download")
                history_file = gr.File(label="Session history download")

            with gr.Accordion("Engine status", open=False):
                gr.Markdown(
                    "Studio owns the normal workflow. Fooocus runs as the hidden local engine at `http://127.0.0.1:7865`. "
                    "Open the raw engine only for debugging with `RUN_FOOOCUS_ENGINE_ONLY.bat`."
                )

            with gr.Accordion("Full reasoning", open=False):
                agent_plan = gr.Markdown(label="Agent plan")

            generation_inputs = [
                goal, image_1, image_2, image_3, wants_identity, wants_exact_edit,
                wants_bundle, vram_gb, primary_prompt, negative_prompt,
            ]
            generation_outputs = [
                generation_status, generation_gallery, latest_result_file, latest_result_path,
                adapter_preview, history_preview, active_job_id,
            ]

            plan_btn.click(
                build_studio_workflow_outputs,
                inputs=[goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle, vram_gb],
                outputs=[
                    agent_plan, primary_prompt, negative_prompt, selected_tool, selected_area,
                    shot_prompts, handoff_recipe, adapter_preview, history_preview,
                ],
                queue=False,
            )
            generate_btn.click(
                submit_studio_generation,
                inputs=generation_inputs,
                outputs=generation_outputs,
                queue=True,
            )
            regenerate_btn.click(
                submit_studio_generation,
                inputs=generation_inputs,
                outputs=generation_outputs,
                queue=True,
            )
            stop_btn.click(stop_studio_generation, outputs=generation_status, queue=False)
            enhance_btn.click(
                submit_studio_enhancement,
                inputs=[latest_result_path, primary_prompt, negative_prompt, vram_gb],
                outputs=generation_outputs,
                queue=True,
            )
            use_reference_btn.click(
                use_latest_result_as_reference,
                inputs=latest_result_path,
                outputs=[image_1, generation_status],
                queue=False,
            )
            open_history_btn.click(open_history_message, outputs=generation_status, queue=False)
            refresh_results_btn.click(
                load_generation_results,
                outputs=[generation_gallery, latest_result_file, latest_result_path, history_preview],
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
                gr.Markdown(value=feature_catalog_markdown())

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
                "1. Double-click `START_HERE.bat` or `RUN_STUDIO_ONE_UI.bat`.\n"
                "2. Work from `http://127.0.0.1:7872`.\n"
                "3. Enter your image goal and optional references.\n"
                "4. Click **Generate in Studio**.\n"
                "5. Review the returned result in the Studio gallery.\n"
                "6. Download, regenerate, enhance, or load the result as Reference 1.\n\n"
                "The raw Fooocus engine stays hidden unless debugging is needed."
            )

    return demo


if __name__ == "__main__":
    build_app().queue().launch(server_name="127.0.0.1", server_port=7872, inbrowser=False)
