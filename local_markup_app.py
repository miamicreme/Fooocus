import gradio as gr

from local_markup.easy_sdxl import build_easy_sdxl_outputs
from local_markup.gradio_helpers import build_markup_ui_outputs
from local_markup.presets import PRESETS, get_preset


WORKFLOWS = ["Generate New Image", "Edit This Image", "Use Image as Reference", "Improve / Enhance"]
AREAS = ["Face", "Glasses", "Hair", "Shirt / Clothes", "Background", "Object", "Whole Image", "I will draw the mask"]


def plan_easy_sdxl(workflow, area, instruction):
    return build_easy_sdxl_outputs(workflow, area, instruction)


def headshot_polo_preset():
    return "Edit This Image", "Shirt / Clothes", "Remove glasses and change suit and tie to a clean navy blue polo shirt"


def understand_edit(instruction):
    prompt, plan = build_markup_ui_outputs(instruction)
    return prompt, plan


def apply_preset(preset_name):
    if not preset_name:
        return "", "", "Choose a preset first."
    preset = get_preset(preset_name)
    instruction = preset["instruction"]
    prompt, plan = build_markup_ui_outputs(instruction)
    return instruction, prompt, plan


def build_app():
    with gr.Blocks(title="Easy SDXL Control Center") as demo:
        gr.Markdown(
            "# Easy SDXL Control Center\n"
            "Use simple choices on top while keeping Fooocus SDXL concepts underneath: Inpaint, Image Prompt, Enhance, steps, CFG, denoise, seed, styles, and LoRAs."
        )
        with gr.Tab("Easy SDXL Planner"):
            gr.Markdown(
                "### Use this as your SDXL copilot\n"
                "For exact edits, use **Edit This Image** and Fooocus **Inpaint or Outpaint**. "
                "For a new picture inspired by the upload, use **Use Image as Reference**."
            )
            with gr.Row():
                with gr.Column():
                    workflow = gr.Radio(label="What are you trying to do?", choices=WORKFLOWS, value="Edit This Image")
                    area = gr.Radio(label="Area / SDXL target", choices=AREAS, value="I will draw the mask")
                    instruction = gr.Textbox(label="Plain-English instruction", placeholder="Example: remove glasses and change the suit to a navy polo shirt", lines=3)
                    with gr.Row():
                        plan_button = gr.Button("Plan SDXL Settings", variant="primary")
                        headshot_button = gr.Button("Headshot: no glasses + polo")
                with gr.Column():
                    settings = gr.Textbox(label="Recommended SDXL settings", lines=4)
                    checklist = gr.Textbox(label="What to do next in Fooocus", lines=10)
            with gr.Row():
                positive_prompt = gr.Textbox(label="Main prompt", lines=4)
                inpaint_prompt = gr.Textbox(label="Inpaint prompt", lines=4)
            with gr.Row():
                detection_prompt = gr.Textbox(label="Detection / mask prompt", lines=2)
                negative_prompt = gr.Textbox(label="Negative prompt", lines=3)

            plan_button.click(
                plan_easy_sdxl,
                inputs=[workflow, area, instruction],
                outputs=[positive_prompt, inpaint_prompt, detection_prompt, negative_prompt, settings, checklist],
                queue=False,
            )
            headshot_button.click(
                headshot_polo_preset,
                outputs=[workflow, area, instruction],
                queue=False,
            ).then(
                plan_easy_sdxl,
                inputs=[workflow, area, instruction],
                outputs=[positive_prompt, inpaint_prompt, detection_prompt, negative_prompt, settings, checklist],
                queue=False,
            )

        with gr.Tab("Classic Markup Assistant"):
            gr.Markdown("Use this when you only want a quick Fooocus inpaint prompt and a short edit plan.")
            with gr.Row():
                with gr.Column():
                    classic_instruction = gr.Textbox(label="Plain-English edit instruction", lines=3)
                    preset = gr.Dropdown(label="Quick edit preset", choices=list(PRESETS.keys()), value=None)
                    with gr.Row():
                        understand_button = gr.Button("Understand Edit", variant="primary")
                        preset_button = gr.Button("Use Preset")
                with gr.Column():
                    prompt = gr.Textbox(label="Fooocus inpaint prompt", lines=5)
                    plan = gr.Markdown(label="Edit plan")
            understand_button.click(understand_edit, inputs=classic_instruction, outputs=[prompt, plan], queue=False)
            preset_button.click(apply_preset, inputs=preset, outputs=[classic_instruction, prompt, plan], queue=False)
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7871, inbrowser=True)
