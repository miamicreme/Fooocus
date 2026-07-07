import gradio as gr

from local_markup.ai_studio_agent import build_agent_outputs
from local_markup.style_explainer import describe_style_markdown, list_style_names, style_recommendations_for_goal


STYLE_NAMES = list_style_names()


def explain_style(style_name, goal):
    return describe_style_markdown(style_name, goal or "realistic personal photo")


def recommend_styles(goal):
    return style_recommendations_for_goal(goal or "realistic personal photo")


def build_app():
    with gr.Blocks(title="AI Image Studio") as demo:
        gr.Markdown(
            "# AI Image Studio\n"
            "A clean AI-assisted interface for Fooocus workflows. Upload images, describe the goal, and let the agent choose the right workflow before you generate."
        )

        with gr.Tab("Agent Planner"):
            with gr.Row():
                with gr.Column(scale=1):
                    goal = gr.Textbox(
                        label="Tell the agent what you want",
                        placeholder="Example: make me standing in a resort photo wearing swim trunks, keep my face recognizable",
                        lines=5,
                    )
                    wants_identity = gr.Checkbox(label="Preserve identity / same person", value=True)
                    wants_exact_edit = gr.Checkbox(label="Exact edit of uploaded image", value=False)
                    wants_bundle = gr.Checkbox(label="Build a bundle / photoshoot set", value=False)
                    plan_btn = gr.Button("Ask Studio Agent", variant="primary")

                with gr.Column(scale=1):
                    image_1 = gr.Image(label="Reference image 1 - face/source", type="numpy")
                    image_2 = gr.Image(label="Reference image 2 - upper body/style", type="numpy")
                    image_3 = gr.Image(label="Reference image 3 - full body/pose", type="numpy")

            with gr.Row():
                selected_tool = gr.Textbox(label="Selected tool", interactive=False)
                selected_area = gr.Textbox(label="Fooocus area", interactive=False)

            agent_plan = gr.Markdown(label="Agent plan")
            with gr.Row():
                primary_prompt = gr.Textbox(label="Best first shot prompt - copy this to Fooocus first", lines=6)
                negative_prompt = gr.Textbox(label="Negative prompt", lines=6)
            with gr.Row():
                shot_prompts = gr.Textbox(label="Shot-by-shot prompt bundle", lines=12)
                handoff_recipe = gr.Textbox(label="Fooocus hand-off recipe", lines=12)

            plan_btn.click(
                build_agent_outputs,
                inputs=[goal, image_1, image_2, image_3, wants_identity, wants_exact_edit, wants_bundle],
                outputs=[agent_plan, primary_prompt, negative_prompt, selected_tool, selected_area, shot_prompts, handoff_recipe],
                queue=False,
            )

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
                "2. Copy the **Best first shot prompt** into Fooocus first.\n"
                "3. Use the selected Fooocus area shown by the agent.\n"
                "4. Upload the same reference/source images.\n"
                "5. Use the generated negative prompt.\n"
                "6. Generate candidates one shot at a time.\n"
                "7. Return here for the next shot or refinement.\n\n"
                "Next engineering step: add a real adapter so this UI can submit jobs directly to Fooocus or a RunPod backend without using the old Fooocus tabs."
            )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7872, inbrowser=True)
