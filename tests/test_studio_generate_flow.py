from __future__ import annotations

import json
from pathlib import Path

from local_markup.engine_queue_contract import EngineJobKind
from local_markup.local_fooocus_adapter import (
    LocalFooocusAdapter,
    STUDIO_CANCEL_API_NAME,
    STUDIO_ENGINE_API_NAME,
    STUDIO_HEALTH_API_NAME,
)
from local_markup.studio_adapter_contract import AdapterJobStatus, ImageStudioJob, ReferenceImage
from local_markup.studio_generation_history import add_adapter_result_to_history
from local_markup.studio_history import StudioHistoryStore, load_history, save_history
from local_markup.studio_workflow_controller import (
    build_job_from_plan,
    build_studio_workflow_outputs,
    load_generation_results,
    submit_generation_run,
)
from local_markup.ai_studio_agent_v2 import build_agent_plan


class FakeStudioEngineClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def predict(self, payload_json: str, api_name: str):
        self.calls.append((json.loads(payload_json), api_name))
        return self.response


def test_studio_ui_has_generate_controls_health_and_gallery() -> None:
    content = Path("ai_studio_app.py").read_text(encoding="utf-8")

    assert "Generate in Studio" in content
    assert "Check Engine Health" in content
    assert "Stop" in content
    assert "Regenerate" in content
    assert "Enhance" in content
    assert "Use as Reference" in content
    assert "Open in History" in content
    assert "gr.Gallery" in content
    assert "latest_result_path" in content
    assert "submit_studio_generation" in content


def test_controller_builds_normalized_job_settings() -> None:
    plan = build_agent_plan("realistic luxury portrait", image_count=0, wants_identity=True, wants_exact_edit=False, wants_bundle=False)
    job, notes = build_job_from_plan(plan, image_count=0)
    payload = job.normalized_payload()

    assert payload["prompt"] == job.prompt
    assert payload["negative_prompt"] == job.negative_prompt
    assert payload["workflow"] == job.kind.value
    assert "settings" in payload
    assert job.settings["performance"] == "Speed"
    assert notes


def test_local_fooocus_adapter_reports_engine_unavailable_without_handoff(tmp_path) -> None:
    adapter = LocalFooocusAdapter(engine_port=9, job_dir=tmp_path / "jobs", output_dir=tmp_path / "outputs")
    job = ImageStudioJob(
        goal="test",
        prompt="test prompt",
        negative_prompt="bad",
        kind=EngineJobKind.TEXT_TO_IMAGE,
    )

    result = adapter.submit(job)

    assert result.status == AdapterJobStatus.FAILED
    assert "Engine status: unavailable" in result.message
    assert result.job_id
    assert result.metadata["normalized_job_path"].endswith(".json")
    assert result.metadata["required_api"] == STUDIO_ENGINE_API_NAME
    assert result.metadata["cancel_api"] == STUDIO_CANCEL_API_NAME
    assert result.metadata["health_api"] == STUDIO_HEALTH_API_NAME


def test_local_fooocus_adapter_accepts_real_output_paths_from_callable(tmp_path) -> None:
    output_path = tmp_path / "outputs" / "result.png"
    output_path.parent.mkdir(parents=True)
    output_path.write_bytes(b"fake image bytes")

    adapter = LocalFooocusAdapter(
        engine_port=9,
        job_dir=tmp_path / "jobs",
        output_dir=tmp_path / "outputs",
        generate_callable=lambda payload: [str(output_path)],
    )
    adapter.is_engine_running = lambda timeout=1.0: True  # type: ignore[method-assign]
    job = ImageStudioJob(
        goal="test",
        prompt="test prompt",
        negative_prompt="bad",
        kind=EngineJobKind.TEXT_TO_IMAGE,
        references=[ReferenceImage(name="ref.png", path=str(tmp_path / "ref.png"))],
    )

    result = adapter.submit(job)

    assert result.status == AdapterJobStatus.COMPLETED
    assert result.output_paths == [str(output_path)]
    assert result.progress_percent == 100.0
    assert adapter.get_results(result.job_id or "").output_paths == [str(output_path)]


def test_adapter_calls_only_stable_studio_engine_endpoint(tmp_path) -> None:
    output_path = tmp_path / "outputs" / "stable.png"
    output_path.parent.mkdir(parents=True)
    output_path.write_bytes(b"fake image bytes")
    fake_client = FakeStudioEngineClient({"status": "completed", "output_paths": [str(output_path)]})
    adapter = LocalFooocusAdapter(
        job_dir=tmp_path / "jobs",
        output_dir=tmp_path / "outputs",
        client_factory=lambda url: fake_client,
    )
    adapter.is_engine_running = lambda timeout=1.0: True  # type: ignore[method-assign]
    job = ImageStudioJob(goal="test", prompt="prompt", negative_prompt="negative", kind=EngineJobKind.TEXT_TO_IMAGE)

    result = adapter.submit(job)

    assert result.status == AdapterJobStatus.COMPLETED
    assert result.output_paths == [str(output_path)]
    assert fake_client.calls[0][1] == STUDIO_ENGINE_API_NAME
    assert fake_client.calls[0][0]["required_api"] == STUDIO_ENGINE_API_NAME
    assert fake_client.calls[0][0]["prompt"] == "prompt"


def test_adapter_health_calls_only_stable_health_endpoint(tmp_path) -> None:
    fake_client = FakeStudioEngineClient(
        {
            "status": "ok",
            "message": "healthy",
            "apis": [STUDIO_HEALTH_API_NAME, STUDIO_ENGINE_API_NAME, STUDIO_CANCEL_API_NAME],
            "controls_ready": True,
            "worker_ready": True,
            "active_job_count": 0,
        }
    )
    adapter = LocalFooocusAdapter(job_dir=tmp_path / "jobs", client_factory=lambda url: fake_client)
    adapter.is_engine_running = lambda timeout=1.0: True  # type: ignore[method-assign]

    result = adapter.health()

    assert result.status == AdapterJobStatus.COMPLETED
    assert fake_client.calls[0][1] == STUDIO_HEALTH_API_NAME
    assert result.metadata["controls_ready"] == "True"
    assert result.metadata["worker_ready"] == "True"


def test_adapter_does_not_guess_raw_fooocus_gradio_payload_or_outputs() -> None:
    content = Path("local_markup/local_fooocus_adapter.py").read_text(encoding="utf-8")

    assert "view_api" not in content
    assert "full Gradio control payload" not in content
    assert "discover_recent_outputs" not in content
    assert STUDIO_ENGINE_API_NAME in content


def test_fooocus_launch_registers_stable_studio_endpoints() -> None:
    launch_content = Path("launch.py").read_text(encoding="utf-8")
    endpoint_content = Path("local_markup/studio_engine_endpoint.py").read_text(encoding="utf-8")

    assert "install_studio_endpoint_launch_hook" in launch_content
    assert "install_studio_endpoint_launch_hook()" in launch_content
    assert "STUDIO_HEALTH_API" in endpoint_content
    assert "STUDIO_GENERATE_API" in endpoint_content
    assert "STUDIO_CANCEL_API" in endpoint_content
    assert "api_name=STUDIO_HEALTH_API" in endpoint_content
    assert "api_name=STUDIO_GENERATE_API" in endpoint_content
    assert "api_name=STUDIO_CANCEL_API" in endpoint_content


def test_generation_history_persists_output_paths_atomically(tmp_path) -> None:
    job = ImageStudioJob(goal="goal", prompt="prompt", negative_prompt="negative", kind=EngineJobKind.TEXT_TO_IMAGE)
    result = LocalFooocusAdapter(engine_port=9, job_dir=tmp_path / "jobs").cancel("job-1")
    store = add_adapter_result_to_history(StudioHistoryStore(), job, result, image_paths=["outputs/a.png", "outputs/b.png"])
    path = save_history(store, tmp_path / "history.json")
    loaded = load_history(path)
    source = Path("local_markup/studio_history.py").read_text(encoding="utf-8")

    assert loaded.latest(1)[0].image_paths == ["outputs/a.png", "outputs/b.png"]
    assert loaded.latest(1)[0].metadata["output_count"] == "2"
    assert "_HISTORY_WRITE_LOCK" in source
    assert ".replace(output_path)" in source


def test_submit_generation_run_returns_gallery_contract_when_engine_unavailable(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run = submit_generation_run(
        goal="realistic portrait",
        image_1=None,
        image_2=None,
        image_3=None,
        wants_identity=True,
        wants_exact_edit=False,
        wants_bundle=False,
        vram_gb=6,
        prompt_override="",
        negative_prompt_override="",
    )

    assert run.result.status == AdapterJobStatus.FAILED
    assert run.output_paths == []
    assert Path(run.manifest_path).exists()
    assert "Generation status" in run.status_markdown()


def test_existing_plan_outputs_still_work() -> None:
    outputs = build_studio_workflow_outputs("realistic portrait", None, None, None, True, False, False, 6)

    assert len(outputs) == 9
    assert outputs[1]
    assert outputs[2]


def test_load_generation_results_returns_gallery_tuple(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    gallery, downloadable, latest_path, history_markdown = load_generation_results()

    assert gallery == []
    assert downloadable is None
    assert latest_path == ""
    assert "Local Session History" in history_markdown


def test_one_click_verifier_exists() -> None:
    script = Path("scripts/verify_studio_engine.py").read_text(encoding="utf-8")
    launcher = Path("VERIFY_STUDIO_ENGINE.bat").read_text(encoding="utf-8")

    assert STUDIO_HEALTH_API_NAME in script
    assert STUDIO_ENGINE_API_NAME in script
    assert STUDIO_CANCEL_API_NAME in script
    assert "--generate" in script
    assert "verify_studio_engine.py" in launcher
