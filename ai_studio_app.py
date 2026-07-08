import gradio as gr

from local_markup.studio_workflow_controller import build_studio_workflow_outputs
from local_markup.fooocus_feature_playbook import build_feature_reasoning
from local_markup.fooocus_feature_catalog import list_features_markdown
from local_markup.style_explainer import describe_style_markdown, list_style_names, style_recommendations_for_goal
from local_markup.studio_usage_guide import studio_usage_markdown


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
            "Create one strong Fooocus image at a time. The Studio gives you the exact workflow, prompt, negative prompt, reference plan, and copy steps. Fooocus stays open separately as the generation engine."
        )

        with gr.Tab("Studio Agent"):
            gr.Markdown(
                "## 1. Tell the Studio what you want\n"
                "Keep it simple: one image goal, only the references that matter, then generate one first shot in Fooocus before making variations."
            )
            with gr.Accordion("Fast no-friction instructions", open=True):
                gr.Markdown(value=studio_usage_markdown())
            with gr.Row():
                with gr.Column(scale=1):
                    goal = gr.Textbox(
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
                    image_1 = gr.Image(label="Reference 1: main subject, source image, or face", type="numpy")
                    image_2 = gr.Image(label="Reference 2: optional mask, style, or support image", type="numpy")
                    image_3 = gr.Image(label="Reference 3: optional pose, layout, or extra angle", type="numpy")

            gr.Markdown("## 2. Copy into Fooocus in this order")
            with gr.Row():
                selected_tool = gr.Textbox(label="Use this Fooocus workflow", interactive=False)
                selected_area = gr.Textbox(label="Open this Fooocus tab or area", interactive=False)

            with gr.Row():
                primary_prompt = gr.Textbox(label="Step 1: Copy this prompt", lines=7)
                negative_prompt = gr.Textbox(label="Step 2: Copy this negative prompt", lines=7)

            with gr.Row():
                handoff_recipe = gr.Textbox(label="Step 3: Follow these Fooocus setup steps", lines=10)
                shot_prompts = gr.Textbox(label="Use these only after the first result", lines=10)

            with gr.Accordion("Review before generating", open=True):
                adapter_preview = gr.Markdown(label="Adapter preview")
                history_preview = gr.Markdown(label="History preview")

            with gr.Accordion("Full reasoning", open=False):
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
                    style_goal = gr.Textbox(label="Image goal", value="realistic personal photo", lines=3)
                    explain_btn = gr.Button("Explain Style", variant="primary")
                    recommend_btn = gr.Button("Recommend Styles")
                with gr.Column():
                    style_explanation = gr.Markdown()
                    style_recs = gr.Textbox(label="Recommended styles", lines=8)
            explain_btn.click(explain_style, inputs=[style_name, style_goal], outputs=style_explanation, queue=False)
            recommend_btn.click(recommend_styles, inputs=style_goal, outputs=style_recs, queue=False)

        with gr.Tab("Fooocus Hand-Off"):
            gr.Markdown(
                "## Fooocus hand-off\n\n"
                "Keep Fooocus running at `http://127.0.0.1:7865`. This Studio does not generate the image for you yet. It gives you the clean setup so you do not have to guess.\n\n"
                "### Fast workflow\n"
                "1. Open **Studio Agent**.\n"
                "2. Describe one image.\n"
                "3. Upload only the references that matter.\n"
                "4. Click **Build My Fooocus Plan**.\n"
                "5. In Fooocus, open the workflow/tab shown by **Use this Fooocus workflow**.\n"
                "6. Copy **Step 1** prompt.\n"
                "7. Copy **Step 2** negative prompt.\n"
                "8. Follow **Step 3** setup steps.\n"
                "9. Generate one image first.\n"
                "10. Come back for the next shot only after reviewing the first result.\n\n"
                "The preview section is a safe dry-run. It checks the job shape and local history without starting live generation."
            )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7872, inbrowser=True)
