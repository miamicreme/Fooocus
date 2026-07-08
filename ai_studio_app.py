import gradio as gr

from local_markup.studio_workflow_controller import build_studio_workflow_outputs
from local_markup.fooocus_feature_playbook import build_feature_reasoning
from local_markup.fooocus_feature_catalog import list_features_markdown
from local_markup.style_explainer import describe_style_markdown, list_style_names, style_recommendations_for_goal


STYLE_NAMES = list_style_names()


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
    with gr.Blocks(title="AI Image Studio") as demo:
        gr.Markdown(
            "# AI Image Studio\n"
            "Plan one focused Fooocus generation at a time. The Studio chooses the workflow, prompt, negative prompt, shot plan, adapter preview, and hand-off recipe while Fooocus remains the separate generation engine."
        )

        with gr.Tab("Studio Agent"):
            gr.Markdown(
                "## 1. Describe the goal\n"
                "Use this tab to create copy-ready instructions for Fooocus. Generate one shot first, review it, then continue to the next shot."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    goal = gr.Textbox(
                        label="Goal / creative direction",
                        placeholder="Example: make me standing full body near a resort pool, keep my face recognizable, realistic photo",
                        lines=5,
                    )
                    with gr.Accordion("Optional intent switches", open=False):
                        wants_identity = gr.Checkbox(label="Keep the same person / subject from references", value=True)
                        wants_exact_edit = gr.Checkbox(label="Exact edit of uploaded image or masked area", value=False)
                        wants_bundle = gr.Checkbox(label="Build a shot bundle / photoshoot set", value=False)
                        vram_gb = gr.Slider(label="GPU VRAM profile", minimum=4, maximum=24, value=6, step=1)
                    plan_btn = gr.Button("Plan Best Fooocus Workflow", variant="primary")

                with gr.Column(scale=1):
                    image_1 = gr.Image(label="Reference 1 - main subject or source image", type="numpy")
                    image_2 = gr.Image(label="Reference 2 - optional style, mask, or upper-body reference", type="numpy")
                    image_3 = gr.Image(label="Reference 3 - optional full-body, pose, or layout reference", type="numpy")

            gr.Markdown("## 2. Copy these fields into Fooocus")
            with gr.Row():
                selected_tool = gr.Textbox(label="Selected Fooocus workflow", interactive=False)
                selected_area = gr.Textbox(label="Fooocus tab / area to use", interactive=False)

            with gr.Row():
                primary_prompt = gr.Textbox(label="Copy first: Best first shot prompt", lines=7)
                negative_prompt = gr.Textbox(label="Copy second: Negative prompt", lines=7)

            with gr.Row():
                handoff_recipe = gr.Textbox(label="Copy third: Fooocus hand-off recipe", lines=10)
                shot_prompts = gr.Textbox(label="Next shots after first result", lines=10)

            with gr.Accordion("Adapter preview and local history", open=True):
                adapter_preview = gr.Markdown(label="Adapter preview")
                history_preview = gr.Markdown(label="History preview")

            with gr.Accordion("Full agent plan and reasoning", open=True):
                agent_plan = gr.Markdown(label="Agent plan")

            plan_btn.click(
                build_studio_workflow_outputs,
                inputs=[goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle, vram_gb],
                outputs=[agent_plan, primary_prompt, negative_prompt, selected_tool, selected_area, shot_prompts, handoff_recipe, adapter_preview, history_preview],
                queue=False,
            )

        with gr.Tab("Feature Brain"):
            gr.Markdown(
                "## Feature Brain\n"
                "This explains which Fooocus features the agent will use for the current scenario and why."
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
            gr.Markdown("Use this before generating to understand what a Fooocus style will do to the image.")
            with gr.Row():
                with gr.Column():
                    style_name = gr.Dropdown(label="Style", choices=STYLE_NAMES, value="Fooocus Photograph")
                    style_goal = gr.Textbox(label="Goal", value="realistic personal photo", lines=3)
                    explain_btn = gr.Button("Explain Style", variant="primary")
                    recommend_btn = gr.Button("Recommend Styles")
                with gr.Column():
                    style_explanation = gr.Markdown()
                    style_recs = gr.Textbox(label="Recommendations", lines=8)
            explain_btn.click(explain_style, inputs=[style_name, style_goal], outputs=style_explanation, queue=False)
            recommend_btn.click(recommend_styles, inputs=style_goal, outputs=style_recs, queue=False)

        with gr.Tab("Fooocus Hand-Off"):
            gr.Markdown(
                "## Use Fooocus as the engine\n\n"
                "This interface is the planning/control layer. Keep Fooocus running separately at `http://localhost:7865`.\n\n"
                "Recommended workflow:\n"
                "1. Ask the Studio Agent for a plan.\n"
                "2. Review the **Adapter preview and local history** section.\n"
                "3. Copy the **Best first shot prompt** into Fooocus first.\n"
                "4. Use the selected Fooocus area shown by the agent.\n"
                "5. Upload the same reference/source images.\n"
                "6. Use the generated negative prompt.\n"
                "7. Generate candidates one shot at a time.\n"
                "8. Return here for the next shot or refinement.\n\n"
                "The adapter preview is a local dry-run. It prepares the job shape and history preview without directly starting active Fooocus generation."
            )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7872, inbrowser=True)
