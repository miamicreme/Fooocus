from local_markup.easy_sdxl import build_easy_sdxl_outputs, build_easy_sdxl_plan


def test_easy_sdxl_edit_plan_keeps_sdxl_concepts():
    plan = build_easy_sdxl_plan("Edit This Image", "Glasses", "change the suit to a navy polo shirt")
    assert plan.recommended_tab == "Inpaint or Outpaint"
    assert plan.detection_prompt == "glasses"
    assert "CFG" in plan.checklist or plan.cfg == "4"
    assert "Inpaint" in plan.checklist


def test_easy_sdxl_outputs_order():
    positive, inpaint, detection, negative, settings, checklist = build_easy_sdxl_outputs(
        "Use Image as Reference",
        "Face",
        "professional headshot with natural light",
    )
    assert "professional headshot" in positive
    assert detection == "face"
    assert "Recommended tab" in settings
    assert "Image Prompt" in checklist
    assert isinstance(negative, str)
